pragma solidity 0.8.20;

contract Bank2688 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
