pragma solidity 0.5.12;

contract Locker7482 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return total; }
}
