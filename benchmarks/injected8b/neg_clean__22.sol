pragma solidity 0.8.20;

contract Pool3856 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function ownerOf_() public view returns (address) { return owner; }
}
