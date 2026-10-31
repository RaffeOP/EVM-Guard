pragma solidity 0.8.20;

contract Bank8633 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
