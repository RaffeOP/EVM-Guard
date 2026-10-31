pragma solidity 0.5.12;

contract Fund7638 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }
}
